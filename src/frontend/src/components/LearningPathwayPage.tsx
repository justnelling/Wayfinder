import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Plus, Minus, RotateCcw } from "lucide-react";
import Tree from "react-d3-tree";
import LearningNode from "./LearningNode";

// First, define our data types clearly
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

// Define the structure react-d3-tree expects
interface D3TreeNode {
  name: string;
  children?: D3TreeNode[];
  nodeDatum?: LearningNodeData;
}

const LearningPathwayPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, learningPathway } = location.state || {};
  const [selectedNode, setSelectedNode] = useState<LearningNodeData | null>(
    null
  );
  const [zoomLevel, setZoomLevel] = useState(1);

  if (!learningPathway) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold text-gray-900">
          No learning pathway found
        </h1>
        <p className="mt-4">Please generate a learning pathway first.</p>
      </div>
    );
  }

  // Convert our data structure to react-d3-tree format
  const convertToTreeFormat = (node: LearningNodeData): D3TreeNode => ({
    name: node.title,
    children: node.sub_nodes.map(convertToTreeFormat),
    nodeDatum: node,
  });

  const treeData = convertToTreeFormat(learningPathway);

  const treeContainerStyle = {
    width: "100%",
    height: "100%",
    fontFamily:
      "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
  };

  // Custom node renderer with improved styling
  const renderCustomNode = ({ nodeDatum }: { nodeDatum: D3TreeNode }) => (
    <g
      onClick={() => {
        if (nodeDatum.nodeDatum) {
          setSelectedNode(nodeDatum.nodeDatum);
        }
      }}
      className="cursor-pointer"
    >
      {/* Larger circle background for the node */}
      <circle r={30} fill="#1e40af" />

      {/* Add a white border/stroke */}
      <circle r={30} fill="none" stroke="white" strokeWidth={2} />

      {/* Text styling */}
      <text
        fill="white"
        x={40}
        y={0}
        dy=".35em"
        style={{
          fontSize: "14px",
          fontWeight: 500,
          fontFamily: "'Inter', sans-serif",
          textShadow: "1px 1px 1px rgba(0,0,0,0.2)",
        }}
        className="select-none"
      >
        {nodeDatum.name}
      </text>
    </g>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate("/")}
                className="mr-4 p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft size={24} />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">
                Your Learning Pathway
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex flex-col h-[calc(100vh-4rem)]">
        {/* Profile summary */}
        <div className="bg-white shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Pathway Overview
          </h2>
          <div className="grid grid-cols-2 gap-4 bg-blue-50 p-4 rounded-lg">
            <div>
              <h3 className="font-medium text-blue-900">Goal</h3>
              <p className="text-blue-800">{profile?.life_path}</p>
            </div>
            <div>
              <h3 className="font-medium text-blue-900">Current Level</h3>
              <p className="text-blue-800">{profile?.skill_level}</p>
            </div>
          </div>
        </div>

        {/* Tree visualization and details panel */}
        <div className="flex flex-1 overflow-hidden relative">
          {/* Tree view */}
          <div className="w-2/3 h-full bg-white border-r">
            <div style={treeContainerStyle}>
              <Tree
                data={treeData}
                orientation="horizontal"
                renderCustomNodeElement={renderCustomNode}
                nodeSize={{ x: 300, y: 200 }}
                separation={{ siblings: 2.5, nonSiblings: 3 }}
                pathFunc="step"
                translate={{ x: 100, y: 200 }}
                zoom={zoomLevel}
                enableLegacyTransitions={true}
                transitionDuration={800}
                pathClassFunc={() => "stroke-blue-500 stroke-2"}
              />
            </div>

            {/* Zoom controls */}
            <div className="absolute bottom-4 right-4 flex gap-2">
              <button
                onClick={() => setZoomLevel((prev) => Math.min(prev + 0.2, 2))}
                className="bg-white p-2 rounded-full shadow hover:bg-gray-50"
                title="Zoom in"
              >
                <Plus size={20} />
              </button>
              <button
                onClick={() =>
                  setZoomLevel((prev) => Math.max(prev - 0.2, 0.5))
                }
                className="bg-white p-2 rounded-full shadow hover:bg-gray-50"
                title="Zoom out"
              >
                <Minus size={20} />
              </button>
              <button
                onClick={() => setZoomLevel(1)}
                className="bg-white p-2 rounded-full shadow hover:bg-gray-50"
                title="Reset zoom"
              >
                <RotateCcw size={20} />
              </button>
            </div>
          </div>

          {/* Details panel */}
          <div className="w-1/3 overflow-y-auto">
            {selectedNode ? (
              <div className="p-6">
                <LearningNode node={selectedNode} />
              </div>
            ) : (
              <div className="p-6 text-gray-500">
                Click a node to view its details
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default LearningPathwayPage;
