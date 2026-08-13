import FactorsSection from "./FactorsSection";
import PredictionsSection from "./PredictionsSection";
import SettingsSection from "./SettingsSection";

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

export default function OverviewTab() {
    return (
        <>
            <FactorsSection factors={factors} />
            <SettingsSection />
            <PredictionsSection predictions={predictions} />
        </>
    );
}
