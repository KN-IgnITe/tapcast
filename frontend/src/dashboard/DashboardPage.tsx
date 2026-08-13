import OverviewTab from "./OverviewTab";
import Sidebar from "../components/Sidebar";
import TabLayout from "./TabLayout";

export default function DashboardPage() {
    return (
        <div className="flex h-screen w-screen bg-gray-100">
            <Sidebar />

            {/* hardcoded content */}
            <TabLayout header="Dashboard">
                <OverviewTab />
            </TabLayout>
        </div>
    );
}
