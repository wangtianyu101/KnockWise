/**
 * LiveKitVoice — full-duplex audio component.
 * Publishes user mic continuously, subscribes to AI audio track.
 * No PTT button — always-on, like a phone call.
 * Compatible with livekit-client v2.x
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { Room, RoomEvent, Track, RemoteTrackPublication } from "livekit-client";

type VoiceState = "connecting" | "connected" | "listening" | "speaking" | "disconnected" | "error";

interface Props {
  roomName: string;
  token: string;
  onTranscript?: (text: string, speaker: "ai" | "user") => void;
  onStateChange?: (state: VoiceState) => void;
}

export default function LiveKitVoice({ roomName, token, onTranscript, onStateChange }: Props) {
  const [state, setState] = useState<VoiceState>("connecting");
  const roomRef = useRef<Room | null>(null);

  const updateState = useCallback((s: VoiceState) => {
    setState(s);
    onStateChange?.(s);
  }, [onStateChange]);

  useEffect(() => {
    if (!roomName || !token) return;

    const room = new Room({
      audioCaptureDefaults: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    roomRef.current = room;

    const connect = async () => {
      try {
        updateState("connecting");

        // Track subscriptions — v2 uses RoomEvent
        room.on(RoomEvent.TrackSubscribed, (track: RemoteTrackPublication) => {
          if (track.kind === Track.Kind.Audio && track.track) {
            updateState("speaking");
            const el = track.track.attach();
            el.setAttribute("autoplay", "true");
            document.getElementById("ai-audio-sink")?.appendChild(el);
          }
        });

        room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrackPublication) => {
          if (track.kind === Track.Kind.Audio) {
            updateState("listening");
          }
        });

        // Connection events
        room.on(RoomEvent.Connected, () => {
          updateState("connected");
          updateState("listening");
        });

        room.on(RoomEvent.Disconnected, () => {
          updateState("disconnected");
        });

        // Local participant events
        room.on(RoomEvent.LocalTrackPublished, () => {
          // Mic track is being sent
        });

        const lkUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880";
        await room.connect(lkUrl, token);

        // Auto-enable microphone
        await room.localParticipant.setMicrophoneEnabled(true);

      } catch (err) {
        console.error("LiveKitVoice connect error:", err);
        updateState("error");
      }
    };

    connect();

    return () => {
      room.disconnect();
      roomRef.current = null;
    };
  }, [roomName, token]);

  const stateLabel: Record<VoiceState, string> = {
    connecting: "连接中...",
    connected: "已连接",
    listening: "正在聆听...",
    speaking: "面试官说话中",
    disconnected: "已断开",
    error: "连接失败",
  };

  const stateColor: Record<VoiceState, string> = {
    connecting: "text-amber-400",
    connected: "text-emerald-400",
    listening: "text-emerald-400",
    speaking: "text-indigo-400",
    disconnected: "text-gray-500",
    error: "text-red-400",
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div id="ai-audio-sink" className="hidden" />
      <div className={`flex items-center gap-2 text-sm ${stateColor[state]}`}>
        <span className={`w-2 h-2 rounded-full inline-block ${
          state === "speaking" ? "bg-indigo-400 animate-pulse" :
          state === "listening" ? "bg-emerald-400" :
          state === "connecting" ? "bg-amber-400 animate-pulse" :
          "bg-gray-500"
        }`} />
        <span className="text-xs">{stateLabel[state]}</span>
      </div>
      <div className="text-xs text-gray-500">
        🎤 {state === "listening" ? "麦克风已开启，请自由说话" :
            state === "speaking" ? "面试官正在说话..." :
            state === "connecting" ? "正在建立连接..." : ""}
      </div>
    </div>
  );
}
