import { useState, useEffect } from "react";
import type { DragEvent } from "react";
import "./App.css";

type Joke = {
    setup: string;
    punchline: string;
};

export function Joke({ joke }: { joke: Joke | null }) {
    if (!joke)
        return (
            <p className="text-gray-500 animate-pulse">Ładowanie żartu...</p>
        );

    return (
        <div className="mt-6 p-4 bg-white rounded-xl shadow-md border border-gray-100">
            <p className="font-medium text-gray-800 italic">"{joke.setup}"</p>
            <p className="mt-2 font-bold text-indigo-600">{joke.punchline}</p>
        </div>
    );
}

export function FileUpload() {
    const [isDragging, setIsDragging] = useState<boolean>(false);
    const [file, setFile] = useState<File | null>(null);
    const [responseMessage, setResponseMessage] = useState<string>("");

    const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault(); // To nie dla przeglądarki SPADUWA
        setIsDragging(true);
    };

    const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const droppedFile = e.dataTransfer.files[0];

            if (droppedFile.name.endsWith(".xlsx")) {
                setFile(droppedFile);
                setResponseMessage("Plik gotowy do wysłania.");
            } else {
                setFile(null);
                setResponseMessage(
                    "Błąd: Akceptujemy tylko pliki Excel (.xlsx)!",
                );
            }
        }
    };

    const uploadFile = async () => {
        if (!file) return;

        setResponseMessage("Wysyłanie...");

        const formData = new FormData();
        formData.append("file", file); // "file" to klucz, pod którym backend szuka pliku

        try {
            const response = await fetch("backend /api/uploadXLSX", {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                // Zakładamy, że serwer zwraca jakiś tekst lub JSON. Używamy .text() na start.
                const data = await response.text();
                setResponseMessage(`Sukces! Serwer odpowiedział: ${data}`);
            } else {
                setResponseMessage(`Błąd serwera: Kod ${response.status}`);
            }
        } catch (error) {
            setResponseMessage(
                "Błąd sieci. Serwer backendowy prawdopodobnie nie działa.",
            );
            console.error(error);
        }
    };

    return (
        <div className="w-full flex flex-col items-center gap-4 mt-8">
            <h2 className="text-xl font-semibold text-slate-700">
                Import danych
            </h2>

            {/* Strefa Drag and Drop */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`w-full p-10 border-2 border-dashed rounded-xl text-center transition-colors duration-200 cursor-pointer ${
                    isDragging
                        ? "border-emerald-500 bg-emerald-50"
                        : "border-slate-300 bg-white hover:bg-slate-50"
                }`}
            >
                {file ? (
                    <p className="font-semibold text-emerald-600">
                        Wybrano plik: {file.name}
                    </p>
                ) : (
                    <p className="text-slate-500">
                        Przeciągnij i upuść plik{" "}
                        <strong className="text-slate-700">.xlsx</strong> tutaj
                    </p>
                )}
            </div>

            {/* Przycisk wysyłania */}
            <button
                onClick={uploadFile}
                disabled={!file}
                className="px-8 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100 shadow-xl"
            >
                Wyślij plik
            </button>

            {/* Ekran odpowiedzi (Display response on screen) */}
            {responseMessage && (
                <div className="mt-4 p-4 bg-white rounded-xl shadow-sm border border-slate-200 w-full text-center">
                    <p className="text-slate-700 font-medium">
                        {responseMessage}
                    </p>
                </div>
            )}
        </div>
    );
}

function App() {
    const [count, setCount] = useState<number>(0);
    const [joke, setJoke] = useState<Joke | null>(null);

    const getJoke = async () => {
        try {
            const response = await fetch(
                "https://official-joke-api.appspot.com/random_joke",
            );
            const data = await response.json();
            setJoke(data);
        } catch (error) {
            console.error("failed to fetch joke: ", error);
        }
    };

    useEffect(() => {
        // i love react
        const getInitialJoke = async () => {
            try {
                const response = await fetch(
                    "https://official-joke-api.appspot.com/random_joke",
                );
                const data = await response.json();
                setJoke(data);
            } catch (error) {
                console.error("failed to fetch initial joke:", error);
            }
        };

        getInitialJoke();
    }, []);

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 font-sans py-12">
            <div className="w-full max-w-xl flex flex-col gap-6 text-center">
                {/* --- SEKCJA LODZIARNI --- */}
                <span className="text-xl font-semibold text-slate-700">
                    Jaka mamy dziś pogodę?
                </span>

                <div className="flex justify-center gap-4">
                    <button
                        className="px-6 py-2 bg-emerald-500 text-white rounded-full hover:bg-emerald-600 transition-colors shadow-lg"
                        onClick={() => setCount(2317)}
                    >
                        spoko
                    </button>
                    <button
                        className="px-6 py-2 bg-orange-500 text-white rounded-full hover:bg-orange-600 transition-colors shadow-lg"
                        onClick={() => setCount(5)}
                    >
                        meh
                    </button>
                </div>

                <span className="text-lg text-slate-600">
                    Twoja lodziarnia potrzebuje dziś{" "}
                    <strong className="text-indigo-600 text-2xl px-2">
                        {count}
                    </strong>{" "}
                    lodzików
                </span>

                <button
                    className="mt-4 px-8 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:scale-105 transition-transform active:bg-indigo-700 shadow-xl"
                    onClick={getJoke}
                >
                    Nowy żart!
                </button>

                <Joke joke={joke} />

                {/* --- SEKCJA IMPORTU PLIKU --- */}

                {/* Delikatna pozioma linia oddzielająca sekcje */}
                <div className="w-full h-px bg-slate-200 my-2"></div>

                {/* 2. NASZ NOWY KOMPONENT */}
                <FileUpload />
            </div>
        </div>
    );
}

export default App;
