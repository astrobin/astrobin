export interface ListResponseInterface<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}
