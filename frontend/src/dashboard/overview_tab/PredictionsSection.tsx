import Section from "../../components/Section";

type Prediction = { id: number; name: string; category: string; time: string };

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

export default function PredictionsSection({
    predictions,
}: {
    predictions: Prediction[];
}) {
    return (
        <>
            <Section title="PREDICTIONS">
                <PredictionsHeader />
                <PredictionsList predictions={predictions} />
            </Section>
        </>
    );
}
