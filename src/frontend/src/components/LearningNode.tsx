import React, { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  Clock,
  BookOpen,
  Target,
  Key,
  AlertCircle,
} from "lucide-react";

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
  resources: Resources; // Changed this to match the actual structure
  sub_nodes: LearningNodeData[];
  continuation_query?: string;
}

interface LearningNodeProps {
  node: LearningNodeData;
  isLast?: boolean;
}

const LearningNode: React.FC<LearningNodeProps> = ({
  node,
  isLast = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "beginner":
        return "bg-green-100 text-green-800";
      case "intermediate":
        return "bg-yellow-100 text-yellow-800";
      case "advanced":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="relative">
      <div className={`flex flex-col ${!isLast ? "mb-4" : ""}`}>
        {/* Main node content */}
        <div
          className="flex items-start bg-white rounded-lg shadow-md p-4 cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => setShowDetails(!showDetails)}
        >
          <div className="mr-2">
            {node.sub_nodes.length > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className="p-1 hover:bg-gray-100 rounded"
              >
                {isExpanded ? (
                  <ChevronDown size={20} />
                ) : (
                  <ChevronRight size={20} />
                )}
              </button>
            )}
          </div>

          <div className="flex-1">
            <div className="flex items-center">
              <h3 className="text-lg font-semibold">{node.title}</h3>
              <span
                className={`ml-3 px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(
                  node.difficulty
                )}`}
              >
                {node.difficulty}
              </span>
            </div>

            {showDetails && (
              <div className="mt-4 space-y-4">
                <div>
                  <p className="text-gray-600">{node.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center text-sm text-gray-600 mb-2">
                      <Clock size={16} className="mr-2" />
                      <span>{node.estimated_duration}</span>
                    </div>

                    <div className="flex items-start mb-2">
                      <Key size={16} className="mr-2 mt-1" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-600">
                          Key Concepts
                        </h4>
                        <ul className="list-disc pl-4 text-sm">
                          {node.key_concepts.map((concept, idx) => (
                            <li key={idx}>{concept}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-start mb-2">
                      <Target size={16} className="mr-2 mt-1" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-600">
                          Learning Objectives
                        </h4>
                        <ul className="list-disc pl-4 text-sm">
                          {node.learning_objectives.map((objective, idx) => (
                            <li key={idx}>{objective}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {node.prerequisites.length > 0 && (
                      <div className="flex items-start mb-2">
                        <AlertCircle size={16} className="mr-2 mt-1" />
                        <div>
                          <h4 className="text-sm font-medium text-gray-600">
                            Prerequisites
                          </h4>
                          <ul className="list-disc pl-4 text-sm">
                            {node.prerequisites.map((prereq, idx) => (
                              <li key={idx}>{prereq}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {node.resources.results.length > 0 && ( // Updated to use resources.results
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2 flex items-center">
                      <BookOpen size={16} className="mr-2" />
                      Resources
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {node.resources.results.map(
                        (
                          resource,
                          idx // Updated to use resources.results
                        ) => (
                          <a
                            key={idx}
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                          >
                            <div className="font-medium">{resource.title}</div>
                            {resource.description && (
                              <div className="text-sm text-gray-600 mt-1">
                                {resource.description}
                              </div>
                            )}
                          </a>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sub-nodes */}
        {isExpanded && node.sub_nodes.length > 0 && (
          <div className="ml-8 mt-4">
            {node.sub_nodes.map((subNode, index) => (
              <LearningNode
                key={index}
                node={subNode}
                isLast={index === node.sub_nodes.length - 1}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningNode;
