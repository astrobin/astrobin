export interface PaginatedApiResultInterface<T> {
  count: number;
  next: string | null;
  prev: string | null;
  results: T[];
}
