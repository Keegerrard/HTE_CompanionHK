import { ChatShell } from "@/features/chat/chat-shell";

export default function Home() {
  return (
    <div className="min-h-dvh flex flex-col bg-background">
      <ChatShell />
    </div>
  );
}
