import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

// Sample learning pathway data with 3 levels
const sampleLearningPathway = {
  title: "Full Stack Web Development",
  description: "Comprehensive path to becoming a full stack developer",
  learning_objectives: [
    "Build complete web applications",
    "Master both frontend and backend development",
    "Deploy and maintain production applications",
  ],
  difficulty: "intermediate",
  prerequisites: ["Basic computer knowledge", "Problem-solving skills"],
  estimated_duration: "6 months",
  key_concepts: ["Web Development", "Programming", "Databases", "DevOps"],
  resources: {
    results: [
      {
        title: "Getting Started with Web Development",
        url: "https://example.com/web-dev-intro",
        type: "course",
        description: "Introduction to web development fundamentals",
      },
    ],
  },
  sub_nodes: [
    // Level 2 - Frontend Development
    {
      title: "Frontend Development",
      description: "Master modern frontend development technologies",
      learning_objectives: [
        "Build responsive user interfaces",
        "Implement modern JavaScript features",
        "Handle state management",
      ],
      difficulty: "intermediate",
      prerequisites: ["HTML basics", "CSS basics"],
      estimated_duration: "2 months",
      key_concepts: ["React", "State Management", "API Integration"],
      resources: {
        results: [
          {
            title: "Modern Frontend Development",
            url: "https://example.com/frontend",
            type: "course",
            description: "Complete guide to frontend development",
          },
        ],
      },
      sub_nodes: [
        // Level 3 nodes for Frontend
        {
          title: "React Fundamentals",
          description: "Core concepts of React development",
          learning_objectives: [
            "Component lifecycle",
            "Hooks",
            "Props & State",
          ],
          difficulty: "beginner",
          prerequisites: ["JavaScript basics"],
          estimated_duration: "2 weeks",
          key_concepts: ["JSX", "Components", "Virtual DOM"],
          resources: {
            results: [
              {
                title: "React Basics",
                url: "https://example.com/react-basics",
                type: "tutorial",
                description: "Getting started with React",
              },
            ],
          },
          sub_nodes: [],
        },
        {
          title: "State Management",
          description: "Advanced state management in React",
          learning_objectives: ["Redux", "Context API", "State Patterns"],
          difficulty: "intermediate",
          prerequisites: ["React basics"],
          estimated_duration: "2 weeks",
          key_concepts: ["Redux", "Context", "State Patterns"],
          resources: {
            results: [
              {
                title: "State Management in React",
                url: "https://example.com/state-management",
                type: "tutorial",
                description: "Mastering state management",
              },
            ],
          },
          sub_nodes: [],
        },
      ],
    },
    // Level 2 - Backend Development
    {
      title: "Backend Development",
      description: "Learn server-side programming and databases",
      learning_objectives: [
        "Build REST APIs",
        "Design databases",
        "Handle authentication",
      ],
      difficulty: "intermediate",
      prerequisites: ["Programming basics"],
      estimated_duration: "2 months",
      key_concepts: ["APIs", "Databases", "Authentication"],
      resources: {
        results: [
          {
            title: "Backend Development Guide",
            url: "https://example.com/backend",
            type: "course",
            description: "Complete guide to backend development",
          },
        ],
      },
      sub_nodes: [
        // Level 3 nodes for Backend
        {
          title: "Node.js & Express",
          description: "Building APIs with Node.js",
          learning_objectives: ["RESTful APIs", "Middleware", "Routing"],
          difficulty: "beginner",
          prerequisites: ["JavaScript"],
          estimated_duration: "2 weeks",
          key_concepts: ["Express", "Middleware", "REST"],
          resources: {
            results: [
              {
                title: "Node.js Essentials",
                url: "https://example.com/nodejs",
                type: "tutorial",
                description: "Learning Node.js and Express",
              },
            ],
          },
          sub_nodes: [],
        },
        {
          title: "Database Design",
          description: "Working with SQL and NoSQL databases",
          learning_objectives: ["SQL", "MongoDB", "Data Modeling"],
          difficulty: "intermediate",
          prerequisites: ["Basic backend knowledge"],
          estimated_duration: "2 weeks",
          key_concepts: ["SQL", "NoSQL", "ORMs"],
          resources: {
            results: [
              {
                title: "Database Fundamentals",
                url: "https://example.com/databases",
                type: "course",
                description: "Understanding database design",
              },
            ],
          },
          sub_nodes: [],
        },
      ],
    },
    // Level 2 - DevOps & Deployment
    {
      title: "DevOps & Deployment",
      description: "Learn to deploy and maintain applications",
      learning_objectives: [
        "Deploy applications",
        "Set up CI/CD pipelines",
        "Monitor production apps",
      ],
      difficulty: "advanced",
      prerequisites: ["Frontend & Backend basics"],
      estimated_duration: "2 months",
      key_concepts: ["DevOps", "CI/CD", "Cloud Services"],
      resources: {
        results: [
          {
            title: "DevOps Handbook",
            url: "https://example.com/devops",
            type: "book",
            description: "Complete guide to DevOps practices",
          },
        ],
      },
      sub_nodes: [
        // Level 3 nodes for DevOps
        {
          title: "Cloud Deployment",
          description: "Deploying applications to the cloud",
          learning_objectives: ["AWS", "Heroku", "Docker"],
          difficulty: "intermediate",
          prerequisites: ["Basic DevOps knowledge"],
          estimated_duration: "2 weeks",
          key_concepts: ["Cloud Services", "Containers", "Deployment"],
          resources: {
            results: [
              {
                title: "Cloud Deployment Guide",
                url: "https://example.com/cloud",
                type: "tutorial",
                description: "Learn cloud deployment",
              },
            ],
          },
          sub_nodes: [],
        },
        {
          title: "CI/CD Pipeline",
          description: "Setting up continuous integration",
          learning_objectives: ["GitHub Actions", "Jenkins", "Testing"],
          difficulty: "advanced",
          prerequisites: ["Cloud deployment"],
          estimated_duration: "2 weeks",
          key_concepts: ["CI/CD", "Automation", "Testing"],
          resources: {
            results: [
              {
                title: "CI/CD Mastery",
                url: "https://example.com/cicd",
                type: "course",
                description: "Master CI/CD pipelines",
              },
            ],
          },
          sub_nodes: [],
        },
      ],
    },
  ],
};

// Sample user profile
const sampleProfile = {
  life_path: "Full Stack Developer",
  skill_level: "beginner",
  interests: ["Web Development", "Programming", "Design"],
  time_commitment: "20 hours per week",
  geographical_context: "Remote",
  learning_style: "hands-on",
  prior_experience: ["Basic HTML", "Basic JavaScript"],
  goals: ["Build web applications", "Get a developer job"],
  constraints: ["Limited time", "Self-paced learning"],
  motivation: "Career change into tech industry",
};

// Test Component
const TestHarness: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const handleViewPathway = () => {
    try {
      navigate("/learning-pathway", {
        state: {
          profile: sampleProfile,
          learningPathway: sampleLearningPathway,
        },
        replace: true,
      });
    } catch (err) {
      setError("Error navigating to pathway: " + (err as Error).message);
    }
  };

  const handleSimulateError = () => {
    navigate("/learning-pathway", {
      state: {
        profile: sampleProfile,
        learningPathway: null, // This should trigger error handling
      },
    });
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Learning Pathway Test Harness</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <button
          onClick={handleViewPathway}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          View Sample Pathway
        </button>

        <button
          onClick={handleSimulateError}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 ml-4"
        >
          Simulate Error
        </button>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Sample Data Preview:</h2>
        <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96">
          {JSON.stringify(
            { profile: sampleProfile, pathway: sampleLearningPathway },
            null,
            2
          )}
        </pre>
      </div>
    </div>
  );
};

export default TestHarness;
