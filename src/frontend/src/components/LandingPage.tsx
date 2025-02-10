import React, { useState, useEffect, useRef } from "react";
import { Send, Menu, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

// Type definitions
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

interface ResourceItem {
  title: string;
  url: string;
  type: string;
  description?: string;
}

interface Resources {
  results: ResourceItem[];
}

interface LearningNodeData {
  title: string;
  description: string;
  learning_objectives: string[];
  difficulty: string;
  prerequisites: string[];
  estimated_duration: string;
  key_concepts: string[];
  resources: Resources;
  sub_nodes: LearningNodeData[];
  continuation_query?: string;
}

interface WebSocketResponse {
  type:
    | "question"
    | "error"
    | "complete"
    | "profile_update"
    | "generating_pathway";
  content?: string;
  learning_pathway?: LearningNodeData | string;
  profile?: UserProfile | string;
}

// Loading Modal Component
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

// Main LandingPage Component
const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>("");
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/chat");

    ws.onopen = () => {
      console.log("WebSocket connection established");
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketResponse = JSON.parse(event.data);
        console.log("Received WebSocket message:", data);

        switch (data.type) {
          case "question":
          case "error":
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: data.content || "An error occurred",
              },
            ]);
            if (data.type === "error") {
              setError(data.content || "An unknown error occurred");
            }
            break;

          case "profile_update":
            if (data.profile) {
              const profileData =
                typeof data.profile === "string"
                  ? JSON.parse(data.profile)
                  : data.profile;
              setProfile(profileData);
              console.log("Profile updated:", profileData);
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
            if (data.learning_pathway && data.profile) {
              try {
                // Parse the learning pathway data if it's a string
                const pathway =
                  typeof data.learning_pathway === "string"
                    ? JSON.parse(data.learning_pathway)
                    : data.learning_pathway;

                // Parse the profile data if it's a string
                const profileData =
                  typeof data.profile === "string"
                    ? JSON.parse(data.profile)
                    : data.profile;

                console.log("Navigating with data:", {
                  profile: profileData,
                  learningPathway: pathway,
                });

                // Navigate to the learning pathway page
                navigate("/learning-pathway", {
                  state: {
                    profile: profileData,
                    learningPathway: pathway,
                  },
                  replace: true,
                });
              } catch (error) {
                console.error("Error processing pathway data:", error);
                setError("Failed to process learning pathway data");
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content:
                      "Sorry, there was an error processing your learning pathway. Please try again.",
                  },
                ]);
              }
            } else {
              console.error("Missing required data:", {
                hasPathway: !!data.learning_pathway,
                hasProfile: !!data.profile,
              });
              setError("Missing required pathway or profile data");
            }
            break;

          default:
            console.warn("Unknown message type received:", data.type);
        }
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
        setError("Failed to process server response");
      }
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
      setError("Connection to server lost");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setError("Connection error occurred");
    };

    setWsConnection(ws);

    return () => {
      ws.close();
    };
  }, [navigate]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    if (!wsConnection || wsConnection.readyState !== WebSocket.OPEN) {
      setError("Connection to server lost. Please refresh the page.");
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: inputValue }]);
    wsConnection.send(inputValue);
    setInputValue("");
    setError(null); // Clear any previous errors when sending new message
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

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

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
                  disabled={isGenerating}
                />
                <button
                  type="submit"
                  className={`p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isGenerating ? "opacity-50 cursor-not-allowed" : ""
                  }`}
                  disabled={isGenerating}
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
