
import hashlib

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "24f3000207@ds.study.iitm.ac.in"

TOOLS = [
    {
        "name": "solve_challenge",
        "description": "Solve the current exam challenge from the HTTP headers.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            },
            status_code=400
        )

    # Notifications have no request ID and must not receive a JSON-RPC body.
    if "id" not in body:
        return Response(status_code=202)

    request_id = body["id"]
    method = body.get("method")
    params = body.get("params") or {}

    if method == "initialize":
        result = {
            "protocolVersion": params.get(
                "protocolVersion", "2025-03-26"
            ),
            "capabilities": {
                "tools": {"listChanged": False}
            },
            "serverInfo": {
                "name": "q14-live-mcp",
                "version": "1.0.0"
            }
        }

    elif method == "ping":
        result = {}

    elif method == "tools/list":
        result = {"tools": TOOLS}

    elif method == "tools/call":
        if params.get("name") != "solve_challenge":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Unknown tool"
                }
            })

        # Read the challenge from the HTTP headers, not the JSON body.
        challenge = request.headers.get("x-exam-challenge")

        if not challenge:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing X-Exam-Challenge header"
                }
            })

        normalized_email = EMAIL.strip().lower()
        value = f"{challenge}:{normalized_email}"
        answer = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

        result = {
            "content": [
                {
                    "type": "text",
                    "text": answer
                }
            ]
        }

    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    })


# Support deployments that route requests to the root path as well.
@app.post("/")
async def root_endpoint(request: Request):
    return await mcp_endpoint(request)
