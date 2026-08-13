import Section from "../components/Section";

type Prediction = { id: number; name: string; category: string; time: string };

function FactorsSection({ factors }: { factors: string[] }) {
    return (
        <>
            <Section title="FACTORS">
                <div className="flex flex-wrap gap-2">
                    {factors.map((factor, index) => (
                        <span
                            key={index}
                            className="text-xs font-medium px-3 py-1.5 rounded-2xl transition-colors bg-gray-50/50 border border-gray-200/60 hover:bg-white hover:border-gray-300 cursor-default"
                        >
                            {factor}
                        </span>
                    ))}
                </div>
            </Section>
        </>
    );
}

function SettingsSection() {
    return (
        <>
            <Section title="SETTINGS">
                <div className="flex w-full gap-5">
                    <div className="bg-gray-200 h-60 w-full rounded-2xl"></div>
                    <div className="h-60 w-full"></div>
                </div>
            </Section>
        </>
    );
}

function PredictionsHeader() {
    return (
        <>
            <div className="flex items-center justify-between">
                <div className="flex gap-2 ml-auto">
                    <button className="px-3.5 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100/80 border border-gray-200 rounded-2xl shadow-2xs transition-all active:scale-95 cursor-pointer">
                        Filter
                    </button>
                    <button className="px-3.5 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100/80 border border-gray-200 rounded-2xl shadow-2xs transition-all active:scale-95 cursor-pointer">
                        Sort
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4 px-4 py-1 text-xs font-semibold tracking-wider text-gray-400">
                <span>name</span>
                <span>category</span>
                <span className="text-right">remaining time</span>
            </div>
        </>
    );
}

function PredictionEntry({
    prediction,
    index,
}: {
    prediction: Prediction;
    index: number;
}) {
    return (
        <div
            key={prediction.id || index}
            className="grid grid-cols-3 gap-4 items-center px-4 py-3 bg-gray-50/50 border border-gray-200/60 rounded-xl text-sm transition-all hover:bg-white hover:border-gray-300 hover:shadow-xs"
        >
            <span className="truncate font-medium text-gray-900">
                {prediction.name}
            </span>
            <span className="truncate text-gray-500 font-normal">
                {prediction.category}
            </span>
            <span className="truncate text-right text-gray-400 font-mono text-xs">
                {prediction.time}
            </span>
        </div>
    );
}

function PredictionsList({ predictions }: { predictions: Prediction[] }) {
    return (
        <div
            className="h-70 overflow-y-auto space-y-2 pr-2"
            style={{
                maskImage:
                    "linear-gradient(to bottom, black 80%, transparent 100%)",
                WebkitMaskImage:
                    "linear-gradient(to bottom, black 80%, transparent 100%)",
            }}
        >
            {predictions.map((prediction, index) => (
                <PredictionEntry prediction={prediction} index={index} />
            ))}
        </div>
    );
}

function PredictionsSection({ predictions }: { predictions: Prediction[] }) {
    return (
        <>
            <Section title="PREDICTIONS">
                <PredictionsHeader />
                <PredictionsList predictions={predictions} />
            </Section>
        </>
    );
}

export default function OverviewTab() {
    const factors = [
        "Football match",
        "Heavy rain",
        "International Cat Day",
        "Diddy party",
        "KN IgnITe Anniversary",
        "Piwo with Kicinski",
    ];

    const predictions = [
        { id: 0, name: "Vodka", category: "Alcohol", time: "2 days" },
        { id: 1, name: "Nachos", category: "Snacks", time: "5 days" },
        { id: 2, name: "Cola", category: "Soft drinks", time: "13 days" },
        { id: 3, name: "Vodka", category: "Alcohol", time: "2 days" },
        { id: 4, name: "Nachos", category: "Snacks", time: "5 days" },
        { id: 5, name: "Cola", category: "Soft drinks", time: "13 days" },
        { id: 6, name: "Vodka", category: "Alcohol", time: "2 days" },
        { id: 7, name: "Nachos", category: "Snacks", time: "5 days" },
        { id: 8, name: "Cola", category: "Soft drinks", time: "13 days" },
        { id: 9, name: "Vodka", category: "Alcohol", time: "2 days" },
        { id: 10, name: "Nachos", category: "Snacks", time: "5 days" },
        { id: 11, name: "Cola", category: "Soft drinks", time: "13 days" },
        { id: 12, name: "Vodka", category: "Alcohol", time: "2 days" },
        { id: 13, name: "Nachos", category: "Snacks", time: "5 days" },
        { id: 14, name: "Cola", category: "Soft drinks", time: "13 days" },
    ];

    return (
        <>
            <FactorsSection factors={factors} />
            <SettingsSection />
            <PredictionsSection predictions={predictions} />
        </>
    );
}
