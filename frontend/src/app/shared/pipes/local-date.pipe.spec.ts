import { LocalDatePipe } from "@shared/pipes/local-date.pipe";

describe("LocalDatePipe", () => {
  let pipe: LocalDatePipe;

  beforeAll(() => {
    pipe = new LocalDatePipe();
  });

  it("create an instance", () => {
    expect(pipe).toBeTruthy();
  });

  it("should work", () => {
    expect(pipe.transform("2020-01-01T20:30:00")).toEqual(new Date("2020-01-01T20:30:00Z"));
  });
});
