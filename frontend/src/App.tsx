import { useState, useEffect } from "react";
import "./App.css";
import { FileUpload } from "./components/FileUpload";
import { ProductForecast } from "./components/Productforecast";
import { ActivePredictionFactors } from "./components/ActivePredictionFactors";

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
            <div className="w-full max-w-5xl flex flex-col gap-8 text-center">
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

                <div className="w-full h-px bg-slate-200 my-2"></div>

                <div className="w-full text-left">
                    <ProductForecast
                        plu="SKU-001"
                        productName="Absolut Vodka"
                        category="1L"
                        currentForecast={125}
                        forecastUnit="units"
                        defaultExpanded={true}
                        factors={[
                            {
                                name: "Pub Quiz Night",
                                weight: 15,
                                errorMargin: 5,
                                color: "from-indigo-500 to-indigo-600",
                            },
                            {
                                name: "Historical Base Demand",
                                weight: 75,
                                errorMargin: 0.9,
                                color: "from-blue-400 to-blue-600",
                            },
                            {
                                name: "Weekend Trend",
                                weight: 10,
                                errorMargin: 1.8,
                                color: "from-amber-400 to-amber-500",
                            },
                        ]}
                    />
                    <ProductForecast
                        plu="SKU-001"
                        productName="Orange Juice"
                        category="1L"
                        currentForecast={125}
                        forecastUnit="units"
                        defaultExpanded={true}
                        factors={[
                            {
                                name: "Pub Quiz Night",
                                weight: 15,
                                errorMargin: 5,
                                color: "from-indigo-500 to-indigo-600",
                            },
                            {
                                name: "Historical Base Demand",
                                weight: 75,
                                errorMargin: 0.9,
                                color: "from-blue-400 to-blue-600",
                            },
                            {
                                name: "Weekend Trend",
                                weight: 10,
                                errorMargin: 1.8,
                                color: "from-amber-400 to-amber-500",
                            },
                        ]}
                    />
                </div>

                <div className="w-full h-px bg-slate-200 my-2"></div>
                <ActivePredictionFactors></ActivePredictionFactors>
                <FileUpload />
            </div>
        </div>
    );
}

export default App;
