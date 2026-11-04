"""HTTPS proxy that only tunnels to the two model APIs, like the graders' run-time network. Logs every CONNECT."""
import asyncio
import sys

ALLOWED = {"api.anthropic.com", "api.openai.com"}


async def pipe(reader, writer):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        writer.close()


async def handle(reader, writer):
    request = (await reader.readline()).decode("latin-1").split()
    while (await reader.readline()) not in (b"\r\n", b"\n", b""):
        pass
    host, _, port = (request[1] if len(request) > 1 else "").partition(":")
    allowed = len(request) > 1 and request[0] == "CONNECT" and host in ALLOWED and port == "443"
    print(f"{request[0] if request else '?'} {host}:{port} {'allowed' if allowed else 'blocked'}", flush=True)
    if not allowed:
        writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
        await writer.drain()
        writer.close()
        return
    up_reader, up_writer = await asyncio.open_connection(host, 443)
    writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
    await writer.drain()
    await asyncio.gather(pipe(reader, up_writer), pipe(up_reader, writer))


async def main():
    server = await asyncio.start_server(handle, "0.0.0.0", int(sys.argv[1]) if len(sys.argv) > 1 else 8888)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
