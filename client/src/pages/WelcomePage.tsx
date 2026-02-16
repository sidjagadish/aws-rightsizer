import { Link } from "react-router-dom";

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="w-full max-w-2xl p-8 bg-white rounded-xl shadow">
        <h1 className="text-3xl font-bold text-gray-900">AWS Rightsizer</h1>
        <p className="mt-2 text-gray-600">Phase 2 scaffold (React + Tailwind).</p>

        <div className="mt-6 flex gap-3">
          <Link
            to="/findings"
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Findings
          </Link>

          <Link
            to="/optimization"
            className="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700"
          >
            EC2 Optimization
          </Link>
        </div>
      </div>
    </div>
  );
}
