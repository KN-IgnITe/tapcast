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

function Dashboard() {
    return (
        <div className="min-h-screen p-6 md:p-10 max-w-4xl mx-auto space-y-8 font-sans text-gray-900">
            {/* header */}
            <header className="border-b border-gray-400 pb-4">
                <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
                    Dashboard
                </h1>
            </header>

            {/* factors section */}
            <section className="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-sm space-y-3">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    prediction factors
                </h2>
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
            </section>

            {/* predictions section */}
            <section className="bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm space-y-5">
                {/* controls */}
                <div className="flex items-center justify-between">
                    <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                        Predictions
                    </h2>
                    <div className="flex gap-2">
                        <button className="px-3.5 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100/80 border border-gray-200 rounded-2xl shadow-2xs transition-all active:scale-95 cursor-pointer">
                            Filter
                        </button>
                        <button className="px-3.5 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100/80 border border-gray-200 rounded-2xl shadow-2xs transition-all active:scale-95 cursor-pointer">
                            Sort
                        </button>
                    </div>
                </div>

                {/* table container */}
                <div className="space-y-2">
                    {/* column headers */}
                    <div className="grid grid-cols-3 gap-4 px-4 py-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                        <span>name</span>
                        <span>category</span>
                        <span className="text-right">remaining time</span>
                    </div>

                    {/* list */}
                    <div
                        className="h-70 overflow-y-auto space-y-2 pr-1"
                        style={{
                            maskImage:
                                "linear-gradient(to bottom, black 80%, transparent 100%)",
                            WebkitMaskImage:
                                "linear-gradient(to bottom, black 80%, transparent 100%)",
                        }}
                    >
                        {predictions.map((prediction, index) => (
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
                        ))}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default Dashboard;
