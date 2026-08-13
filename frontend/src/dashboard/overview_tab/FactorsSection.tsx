import Section from "../../components/Section";

export default function FactorsSection({ factors }: { factors: string[] }) {
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
