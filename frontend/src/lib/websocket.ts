import type { WSEvent } from "./types";

type EventHandler = (payload: Record<string, unknown>) => void;

export class ShieldStockWS {
  private ws: WebSocket | null = null;
  private handlers = new Map<string, Set<EventHandler>>();
  private reconnectDelay = 1000;
  private maxDelay = 30_000;
  private shouldClose = false;

  constructor(private url: string) {}

  connect(): void {
    this.shouldClose = false;
    this._connect();
  }

  private _connect(): void {
    if (this.shouldClose) return;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectDelay = 1000;
      };

      this.ws.onmessage = (ev) => {
        try {
          const data: WSEvent = JSON.parse(ev.data as string);
          const subs = this.handlers.get(data.event);
          if (subs) {
            subs.forEach((fn) => fn(data.payload));
          }
          // wildcard handlers
          const wildcards = this.handlers.get("*");
          if (wildcards) {
            wildcards.forEach((fn) => fn({ event: data.event, ...data.payload }));
          }
        } catch {
          // ignore parse errors
        }
      };

      this.ws.onclose = () => {
        if (!this.shouldClose) {
          setTimeout(() => {
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
            this._connect();
          }, this.reconnectDelay);
        }
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      // WebSocket constructor may throw in SSR — ignore
    }
  }

  on(event: string, handler: EventHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }

  close(): void {
    this.shouldClose = true;
    this.ws?.close();
  }
}
