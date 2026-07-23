type LoadingStateProps = {
  message?: string;
};

export function LoadingState({ message = "正在加载..." }: LoadingStateProps) {
  return (
    <p aria-live="polite" className="text-sm text-muted-foreground" role="status">
      {message}
    </p>
  );
}
