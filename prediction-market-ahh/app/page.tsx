import { HomePageContent } from "./components/HomePageContent";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="border-b border-gray-700 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-3xl font-bold text-blue-400">Arby's</h1>
        </div>
      </header>

      <main className="container mx-auto p-4">
        <HomePageContent />
      </main>
    </div>
  );
}
