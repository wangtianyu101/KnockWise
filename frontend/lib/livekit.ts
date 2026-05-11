const LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880";

let livekitToken: string | null = null;

export async function getLiveKitToken(roomName: string, participantName: string): Promise<string> {
  if (livekitToken) return livekitToken;

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/interviews/livekit-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("codemock_token")}` },
    body: JSON.stringify({ room_name: roomName, participant_name: participantName }),
  });

  if (!res.ok) throw new Error("Failed to get LiveKit token");
  const data = await res.json();
  livekitToken = data.token;
  return livekitToken;
}

export function getLiveKitUrl(): string {
  return LIVEKIT_URL;
}
