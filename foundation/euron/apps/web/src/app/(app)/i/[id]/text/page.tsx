import { TextPracticeView } from "@/components/interview/text-practice-view";

export default async function TextPracticePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TextPracticeView id={id} />;
}
