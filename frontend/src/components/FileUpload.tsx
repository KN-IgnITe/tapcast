import { useState } from "react";
import type { DragEvent } from "react";
const apiUrl = "http://localhost:8080";

export function FileUpload() {
    const [isDragging, setIsDragging] = useState<boolean>(false);
    const [file, setFile] = useState<File | null>(null);
    const [responseMessage, setResponseMessage] = useState<string>("");

    const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
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
                setResponseMessage("The file is ready for sending.");
            } else {
                setFile(null);
                setResponseMessage("Error: You can put only Excel file!");
            }
        }
    };

    const uploadFile = async () => {
        if (!file) return;

        setResponseMessage("Sending...");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${apiUrl}/uploadXLSX`, {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                const data = await response.text();
                setResponseMessage(`Success! Server answered: ${data}`);
            } else {
                setResponseMessage(`Server error: Code ${response.status}`);
            }
        } catch (error) {
            setResponseMessage("Network error. Backend out of use!.");
            console.error(error);
        }
    };

    return (
        <div className="w-full flex flex-col items-center gap-4 mt-8">
            <h2 className="text-xl font-semibold text-slate-700">
                Import danych
            </h2>

            {/* Drag and Drop */}
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

            {/* Upload button */}
            <button
                onClick={uploadFile}
                disabled={!file}
                className="px-8 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100 shadow-xl"
            >
                Wyślij plik
            </button>

            {/* Response screen */}
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
