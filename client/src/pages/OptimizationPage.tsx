import { Link } from "react-router-dom";

export default function OptimizationPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-900">EC2 Optimization</h1>
          <Link to="/" className="text-blue-600 hover:underline">
            Back
          </Link>
        </div>

        <div className="mt-4 p-5 bg-white rounded-xl shadow">
          <p className="text-gray-600">
            Scaffold for optimization view. Later: GET <code>/api/instances</code>
          </p>
        </div>
      </div>
    </div>
  );
}
