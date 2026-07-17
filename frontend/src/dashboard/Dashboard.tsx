const factors = [
    "Football match",
    "Heavy rain",
    "International Cat Day",
    "Diddy party",
    "KN IgnITe Anniversary",
    "Piwo with Kicinski",
];

const predictions = [
    { name: "Vodka", category: "Alcohol", time: "2 days" },
    { name: "Nachos", category: "Snacks", time: "5 days" },
    { name: "Cola", category: "Soft drinks", time: "13 days" },
    { name: "Vodka", category: "Alcohol", time: "2 days" },
    { name: "Nachos", category: "Snacks", time: "5 days" },
    { name: "Cola", category: "Soft drinks", time: "13 days" },
    { name: "Vodka", category: "Alcohol", time: "2 days" },
    { name: "Nachos", category: "Snacks", time: "5 days" },
    { name: "Cola", category: "Soft drinks", time: "13 days" },
    { name: "Vodka", category: "Alcohol", time: "2 days" },
    { name: "Nachos", category: "Snacks", time: "5 days" },
    { name: "Cola", category: "Soft drinks", time: "13 days" },
    { name: "Vodka", category: "Alcohol", time: "2 days" },
    { name: "Nachos", category: "Snacks", time: "5 days" },
    { name: "Cola", category: "Soft drinks", time: "13 days" },
];

function Dashboard() {
    return (
        <div>
            <h1 className="text-3xl font-bold m-2 mr-200">dashboard</h1>

            {/* factors */}
            <div className="border-2 rounded-3xl w-fit mx-auto p-2 m-2">
                <h1 className="font-bold">factors</h1>
                <div className="flex flex-wrap w-fit max-w-150">
                    {factors.map((factor) => (
                        <p className="border-2 rounded-3xl px-1 m-1">
                            {factor}
                        </p>
                    ))}
                </div>
            </div>

            {/* prediction list */}
            <div className="px-20">
                <div>
                    <button className="border-2 rounded-3xl m-2 p-2">
                        filter
                    </button>
                    <button className="border-2 rounded-3xl m-2 p-2">
                        sort
                    </button>
                </div>

                <div className="flex justify-between mx-20">
                    <h1 className="font-bold">name</h1>
                    <h1 className="font-bold">category</h1>
                    <h1 className="font-bold">time</h1>
                </div>

                <div
                    className="h-100 overflow-y-auto py-2"
                    style={{
                        maskImage:
                            "linear-gradient(to bottom, transparent, black 10%, black 90%, transparent)",
                        WebkitMaskImage:
                            "linear-gradient(to bottom, transparent, black 10%, black 90%, transparent)",
                    }}
                >
                    {predictions.map((prediction) => (
                        <div className="flex gap-x-4 border-2 m-2 px-2 rounded-2xl">
                            <p>{prediction.name}</p>
                            <p>{prediction.category}</p>
                            <p>{prediction.time}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
