import { useState } from "react";
import type { DragEvent } from "react";

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
            const response = await fetch("/api/uploadXLSX", {
                //todo
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
