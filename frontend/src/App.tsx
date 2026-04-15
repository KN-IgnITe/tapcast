import { useState, useEffect } from "react"
import "./App.css"

type Joke = {
    setup: string
    punchline: string
};

export function Joke({ joke }: { joke: Joke | null }) {
    if (!joke) return <p>Loading joke...</p>

    return (
        <>
            <p>{joke.setup}</p>
            <p>{joke.punchline}</p>
        </>
    );
}

function App() {
    const [count, setCount] = useState<number>(0)
    const [joke, setJoke] = useState<Joke | null>(null)

    const getJoke = async () => {
        try {
            const response = await fetch(
                "https://official-joke-api.appspot.com/random_joke"
            )
            const data = await response.json()
            setJoke(data)
        } catch (error) {
            console.error("failed to fetch joke: ", error)
        }
    };

    useEffect(() => {
        // i love react
        const getInitialJoke = async () => {
            try {
                const response = await fetch(
                    "https://official-joke-api.appspot.com/random_joke"
                )
                const data = await response.json()
                setJoke(data)
            } catch (error) {
                console.error("failed to fetch initial joke:", error)
            }
        }

        getInitialJoke()
    }, [])

    return (
        <div style={{ textAlign: "center", marginTop: "50px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <span>Jaka mamy dzis pogode?</span>
                <div style={{ display: "flex", justifyContent: "center", gap: "10px" }}>
                    <button className="button" onClick={() => setCount(2317)}>
                        spoko
                    </button>
                    <button className="button" onClick={() => setCount(5)}>
                        meh
                    </button>
                </div>
                <span>Twoja lodziarnia potrzebuje dzis {count} lodzikow</span>
                <br />
                <button className="button" onClick={getJoke}>
                    Rzart
                </button>
                <Joke joke={joke} />
            </div>
        </div>
    );
}

export default App;