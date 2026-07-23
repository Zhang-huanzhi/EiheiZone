type EmptyStateProps = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <section className="space-y-2" aria-labelledby="empty-state-title">
      <h2 className="text-lg font-medium" id="empty-state-title">
        {title}
      </h2>
      <p className="text-muted-foreground">{description}</p>
    </section>
  );
}
