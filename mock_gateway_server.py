#!/usr/bin/env python3
"""BeRich 聚合 API 網關與算力協調器 (Open-Source Reference Gateway Server).

本程式為 100% Python 標準庫實現之輕量級聚合網關參考伺服器（零第三方依賴），
用於獨立驗證 `berich_worker.py` 的完整端到端流程：
1. 驗證 Worker OAuth 綁定憑證 (`/api/compute/oauth/verify_worker`)
2. 接收跨平台 Worker 節點註冊、多選訂閱模型掛載與心跳 (`/api/compute/nodes/*`)
3. 開放標準 OpenAI 相容端點 (`/v1/models`, `/v1/chat/completions`) 供外部開發者呼叫
4. 自動將外部請求路由至對應訂閱（Claude / Codex / Gemini）之 Worker 節點並記錄在線互助貢獻
"""

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

PROVIDER_MULTIPLIERS = {
    "claude_code": 12.0,
    "codex": 10.0,
    "gemini_cli": 8.0,
}


class ReferenceGatewayState:
    """記憶體內算力調度與 OpenAI 相容網關狀態機。"""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_events: Dict[str, threading.Event] = {}

    def verify_worker(self, oauth_token: str, node_id: str, provider_type: str, os_name: str) -> Dict[str, Any]:
        providers = [p.strip().lower() for p in provider_type.split(",") if p.strip()]
        if not providers:
            providers = ["claude_code"]
        with self.lock:
            bonus = 50.0 * len(providers)
            existing = self.nodes.get(node_id, {})
            self.nodes[node_id] = {
                "node_id": node_id,
                "node_name": existing.get("node_name", f"{os_name}-{node_id}"),
                "provider_type": providers[0],
                "selected_providers": providers,
                "supported_models": existing.get("supported_models", []),
                "credits_earned": existing.get("credits_earned", 0.0) + bonus,
                "tasks_completed": existing.get("tasks_completed", 0),
                "total_tokens": existing.get("total_tokens", 0),
                "wallet_address": existing.get("wallet_address"),
                "oauth_verified": True,
                "last_seen": time.time(),
            }
            return {
                "status": "verified",
                "node_id": node_id,
                "providers": providers,
                "credits_awarded": bonus,
                "wallet_address": "0x71c000000000000000000000000000000000beef",
            }

    def register_node(
        self,
        node_id: str,
        node_name: str,
        provider_type: str,
        supported_models: List[str],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        with self.lock:
            existing = self.nodes.get(node_id, {})
            selected_provs = metadata.get("selected_providers") or [provider_type]
            self.nodes[node_id] = {
                "node_id": node_id,
                "node_name": node_name,
                "provider_type": provider_type,
                "selected_providers": selected_provs,
                "supported_models": supported_models,
                "metadata": metadata,
                "credits_earned": existing.get("credits_earned", 0.0),
                "tasks_completed": existing.get("tasks_completed", 0),
                "total_tokens": existing.get("total_tokens", 0),
                "wallet_address": existing.get("wallet_address"),
                "last_seen": time.time(),
            }
            return {
                "status": "success",
                "node_id": node_id,
                "credits": self.nodes[node_id]["credits_earned"],
            }

    def bind_wallet(self, node_id: str, wallet_address: str) -> Dict[str, Any]:
        with self.lock:
            if node_id in self.nodes:
                self.nodes[node_id]["wallet_address"] = wallet_address
            return {"status": "success", "node_id": node_id, "wallet_address": wallet_address}

    def heartbeat(self, node_id: str) -> Dict[str, Any]:
        with self.lock:
            if node_id in self.nodes:
                self.nodes[node_id]["last_seen"] = time.time()
            return {"status": "ok", "node_id": node_id}

    def claim_task(self, node_id: str) -> Dict[str, Any]:
        now = time.time()
        with self.lock:
            node = self.nodes.get(node_id)
            if not node:
                return {"has_task": False}
            if node.get("cooldown_until", 0.0) > now:
                return {"has_task": False}
            if node.get("status") == "busy":
                return {"has_task": False}
            # 5 小時滾動視窗 75% 軟上限保護（預留 25% 給號主自用）
            soft_cap = int(node.get("window_soft_limit", 150_000) * node.get("max_share_ratio", 0.75))
            if node.get("window_tokens_used", 0) >= soft_cap:
                return {"has_task": False}
            supported = set(node.get("supported_models") or ["default"])
            prov_cooldowns = node.get("provider_cooldowns") or {}
            for task_id, task in self.tasks.items():
                if task["status"] == "pending":
                    if node_id in task.get("failed_node_ids", []):
                        continue
                    model_lower = task["model"].lower()
                    req_prov = None
                    if "claude" in model_lower:
                        req_prov = "claude_code"
                    elif "gpt" in model_lower or "o3" in model_lower:
                        req_prov = "codex"
                    elif "gemini" in model_lower:
                        req_prov = "gemini_cli"
                    if req_prov and prov_cooldowns.get(req_prov, 0.0) > now:
                        continue
                    if task["model"] in supported or "default" in supported:
                        task["status"] = "processing"
                        task["assigned_node_id"] = node_id
                        task["assigned_at"] = now
                        node["status"] = "busy"
                        return {
                            "has_task": True,
                            "task_id": task_id,
                            "prompt": task["prompt"],
                            "model": task["model"],
                        }
            return {"has_task": False}

    def submit_task(
        self,
        node_id: str,
        task_id: str,
        result: str,
        token_count: int,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        with self.lock:
            task = self.tasks.get(task_id)
            node = self.nodes.get(node_id)
            if not task or not node:
                return {"status": "error", "message": "Task or node not found"}

            if error:
                err_upper = error.upper()
                failed_list = task.setdefault("failed_node_ids", [])
                if node_id not in failed_list:
                    failed_list.append(node_id)
                task["failover_count"] = task.get("failover_count", 0) + 1

                failed_prov = None
                if ":" in error:
                    failed_prov = error.split(":", 1)[1].strip().lower()

                prov_cooldowns = node.setdefault("provider_cooldowns", {})
                if "TASK_YIELDED" in err_upper:
                    node["cooldown_until"] = now + 60.0
                    node["status"] = "online"
                elif "AUTH_REQUIRED" in err_upper:
                    if failed_prov:
                        prov_cooldowns[failed_prov] = now + 86400.0
                    node["cooldown_until"] = now + 3600.0
                    node["status"] = "cooldown"
                elif "RATE_LIMITED_RPM" in err_upper:
                    if failed_prov:
                        prov_cooldowns[failed_prov] = now + 60.0
                    node["cooldown_until"] = now + 60.0
                    node["status"] = "cooldown"
                else:
                    if failed_prov:
                        prov_cooldowns[failed_prov] = now + 1800.0
                    node["cooldown_until"] = now + 1800.0
                    node["status"] = "cooldown"

                # 重新放回 pending，讓下一位在線節點無縫接手
                task["status"] = "pending"
                task["assigned_node_id"] = None
                return {
                    "status": "failover_requeued",
                    "task_id": task_id,
                    "failover_count": task["failover_count"],
                }

            task["status"] = "completed"
            task["result"] = result
            task["token_count"] = token_count
            task["completed_at"] = now
            node["status"] = "online"
            node["window_tokens_used"] = node.get("window_tokens_used", 0) + token_count

            # 根據任務模型計算對應訂閱獎勵倍率
            model_lower = task["model"].lower()
            if "claude" in model_lower:
                mult = PROVIDER_MULTIPLIERS["claude_code"]
            elif "gpt" in model_lower or "o3" in model_lower:
                mult = PROVIDER_MULTIPLIERS["codex"]
            elif "gemini" in model_lower:
                mult = PROVIDER_MULTIPLIERS["gemini_cli"]
            else:
                mult = 10.0

            reward = round((token_count / 1000.0) * mult, 4)
            node["credits_earned"] = round(node["credits_earned"] + reward, 4)
            node["tasks_completed"] += 1
            node["total_tokens"] += token_count

            ev = self.task_events.get(task_id)
            if ev:
                ev.set()

            return {
                "status": "success",
                "task_id": task_id,
                "reward": reward,
                "credits_earned": node["credits_earned"],
            }

    @staticmethod
    def build_stateless_context_prompt(messages: List[Dict[str, str]]) -> str:
        """將 OpenAI 多輪對話完整序列化，確保跨節點 Failover 切換時不會發生多輪對話失憶。"""
        if not messages:
            return "Hello"
        non_sys = [m for m in messages if m.get("role") != "system"]
        sys_msgs = [m.get("content", "").strip() for m in messages if m.get("role") == "system" and m.get("content")]
        if len(non_sys) == 1 and not sys_msgs:
            return non_sys[0].get("content", "").strip() or "Hello"
        lines: List[str] = []
        if sys_msgs:
            lines.append(f"[SYSTEM]\n" + "\n".join(sys_msgs))
        for m in non_sys[-12:]:
            role = (m.get("role") or "user").upper()
            lines.append(f"[{role}]\n{m.get('content', '').strip()}")
        return "\n\n".join(lines)

    def dispatch_openai_chat(self, model: str, messages: List[Dict[str, str]], timeout: float = 15.0) -> Dict[str, Any]:
        prompt = self.build_stateless_context_prompt(messages)
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        ev = threading.Event()

        with self.lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "model": model,
                "prompt": prompt,
                "status": "pending",
                "result": None,
                "token_count": 0,
                "assigned_node_id": None,
                "failed_node_ids": [],
                "failover_count": 0,
                "created_at": time.time(),
            }
            self.task_events[task_id] = ev

        completed = ev.wait(timeout=timeout)
        with self.lock:
            task = self.tasks[task_id]
            self.task_events.pop(task_id, None)
            if not completed or task["status"] != "completed":
                raise TimeoutError(f"Task {task_id} timed out waiting for worker node")

            prompt_tokens = max(10, len(prompt) // 3)
            completion_tokens = max(20, task["token_count"] - prompt_tokens)
            return {
                "id": f"chatcmpl-{task_id}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": task["result"],
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": task["token_count"],
                },
                "berich_routing": {
                    "routed_node_id": task["assigned_node_id"],
                    "auth_mode": "oauth_subscription_sandbox",
                    "task_id": task_id,
                    "failover_count": task.get("failover_count", 0),
                    "failed_over_from": list(task.get("failed_node_ids", [])),
                },
            }


def create_gateway_server(host: str = "127.0.0.1", port: int = 0) -> Tuple[ThreadingHTTPServer, ReferenceGatewayState]:
    state = ReferenceGatewayState()

    class GatewayHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass  # 保持測試輸出乾淨

        def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _read_json(self) -> Dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            return json.loads(body)

        def do_GET(self) -> None:
            if self.path in ("/v1/models", "/api/compute/v1/models"):
                models = set()
                for n in state.nodes.values():
                    models.update(n.get("supported_models") or [])
                self._send_json(
                    {
                        "object": "list",
                        "data": [{"id": m, "object": "model", "owned_by": "berich-oauth-pool"} for m in sorted(models)],
                    }
                )
            elif self.path == "/api/compute/stats":
                self._send_json(
                    {
                        "online_nodes": len(state.nodes),
                        "nodes": list(state.nodes.values()),
                        "total_tasks": len(state.tasks),
                    }
                )
            else:
                self._send_json({"error": "Not found"}, status=404)

        def do_POST(self) -> None:
            payload = self._read_json()
            if self.path == "/api/compute/oauth/verify_worker":
                res = state.verify_worker(
                    oauth_token=payload.get("oauth_token", ""),
                    node_id=payload.get("node_id", "worker-node"),
                    provider_type=payload.get("provider_type", "claude_code"),
                    os_name=payload.get("os_name", "Local"),
                )
                self._send_json(res)
            elif self.path == "/api/compute/nodes/register":
                res = state.register_node(
                    node_id=payload["node_id"],
                    node_name=payload.get("node_name", payload["node_id"]),
                    provider_type=payload.get("provider_type", "claude_code"),
                    supported_models=payload.get("supported_models") or ["default"],
                    metadata=payload.get("metadata") or {},
                )
                self._send_json(res)
            elif self.path == "/api/compute/nodes/bind_wallet":
                res = state.bind_wallet(payload["node_id"], payload["wallet_address"])
                self._send_json(res)
            elif self.path == "/api/compute/nodes/heartbeat":
                res = state.heartbeat(payload["node_id"])
                self._send_json(res)
            elif self.path == "/api/compute/tasks/claim":
                res = state.claim_task(payload["node_id"])
                self._send_json(res)
            elif self.path == "/api/compute/tasks/submit":
                res = state.submit_task(
                    node_id=payload["node_id"],
                    task_id=payload["task_id"],
                    result=payload["result"],
                    token_count=int(payload.get("token_count", 100)),
                    error=payload.get("error"),
                )
                self._send_json(res)
            elif self.path in ("/v1/chat/completions", "/api/compute/v1/chat/completions"):
                auth = self.headers.get("Authorization", "")
                if not auth.startswith("Bearer sk-berich-"):
                    self._send_json({"error": "Missing or invalid Bearer sk-berich-... token"}, status=401)
                    return
                try:
                    res = state.dispatch_openai_chat(
                        model=payload.get("model", "claude-sonnet-5-5"),
                        messages=payload.get("messages", []),
                        timeout=float(payload.get("timeout", 15.0)),
                    )
                    self._send_json(res)
                except Exception as e:
                    self._send_json({"error": str(e)}, status=504)
            else:
                self._send_json({"error": f"Unknown endpoint {self.path}"}, status=404)

    server = ThreadingHTTPServer((host, port), GatewayHandler)
    return server, state
