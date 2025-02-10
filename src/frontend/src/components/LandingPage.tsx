import React, { useState, useEffect, useRef } from "react";
import { Send, Menu, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface UserProfile {
  life_path: string | null;
  skill_level: string | null;
  interests: string[];
  time_commitment: string | null;
  geographical_context: string | null;
  learning_style: string | null;
  prior_experience: string[];
  goals: string[];
  constraints: string[];
  motivation: string | null;
}

interface WebSocketResponse {
  type:
    | "question"
    | "error"
    | "complete"
    | "profile_update"
    | "generating_pathway";
  content?: string;
  learning_pathway?: any;
  profile?: UserProfile;
}

const LoadingModal: React.FC<{ isOpen: boolean }> = ({ isOpen }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl">
        <div className="flex flex-col items-center">
          <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Generating Your Learning Pathway
          </h2>
          <p className="text-gray-600 text-center mb-4">
            Please wait while we create your personalized learning journey based
            on your profile...
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse"></div>
          </div>
          <p className="text-sm text-gray-500">This may take a minute or two</p>
        </div>
      </div>
    </div>
  );
};

const LandingPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>("");
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [learningPathway, setLearningPathway] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/chat");

    ws.onmessage = (event) => {
      const data: WebSocketResponse = JSON.parse(event.data);

      switch (data.type) {
        case "question":
        case "error":
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: data.content || "Error occurred",
            },
          ]);
          break;

        case "profile_update":
          if (data.profile) {
            setProfile(data.profile);
          }
          break;

        case "generating_pathway":
          setIsGenerating(true);
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: data.content || "Generating your learning pathway...",
            },
          ]);
          break;

        case "complete":
          setIsGenerating(false);
          if (data.learning_pathway) {
            setLearningPathway(data.learning_pathway);
          }
          if (data.profile) {
            setProfile(data.profile);
          }
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content:
                "Your profile is complete! I have generated your learning pathway.",
            },
          ]);
          break;
      }
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    setWsConnection(ws);

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    setMessages((prev) => [...prev, { role: "user", content: inputValue }]);
    wsConnection?.send(inputValue);
    setInputValue("");
  };

  const renderProfileField = (key: keyof UserProfile, value: any) => {
    const labels: Record<keyof UserProfile, string> = {
      life_path: "Life Path",
      skill_level: "Skill Level",
      interests: "Interests",
      time_commitment: "Time Commitment",
      geographical_context: "Location",
      learning_style: "Learning Style",
      prior_experience: "Prior Experience",
      goals: "Goals",
      constraints: "Constraints",
      motivation: "Motivation",
    };

    if (Array.isArray(value)) {
      return value.length > 0 ? (
        <div key={key} className="mb-4">
          <h3 className="text-sm font-semibold text-gray-600">{labels[key]}</h3>
          <ul className="pl-4 mt-1">
            {value.map((item, index) => (
              <li key={index} className="text-sm text-gray-900">
                • {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null;
    }

    return value ? (
      <div key={key} className="mb-4">
        <h3 className="text-sm font-semibold text-gray-600">{labels[key]}</h3>
        <p className="text-sm text-gray-900 mt-1">{value}</p>
      </div>
    ) : null;
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <LoadingModal isOpen={isGenerating} />

      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Career Pathfinder
          </h1>
          <Menu className="h-6 w-6 text-gray-500 cursor-pointer" />
        </div>
      </header>

      {/* Main content area */}
      <main className="flex-1 overflow-hidden">
        <div className="h-full flex">
          {/* Chat section */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`mb-4 ${
                    message.role === "user" ? "text-right" : "text-left"
                  }`}
                >
                  <div
                    className={`inline-block p-3 rounded-lg ${
                      message.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-900"
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input form */}
            <div className="p-4 border-t">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <Send className="h-5 w-5" />
                </button>
              </form>
            </div>
          </div>

          {/* Profile section */}
          <div className="w-96 border-l bg-white p-6 overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              Your Profile
            </h2>
            {profile ? (
              Object.entries(profile).map(([key, value]) =>
                renderProfileField(key as keyof UserProfile, value)
              )
            ) : (
              <div className="text-gray-500">
                <p>Start chatting to build your profile...</p>
                <p className="mt-2 text-sm">
                  We'll gather information about your:
                </p>
                <ul className="mt-1 text-sm pl-4">
                  <li>• Career goals</li>
                  <li>• Current skill level</li>
                  <li>• Interests and motivations</li>
                  <li>• Learning preferences</li>
                  <li>• Time availability</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
