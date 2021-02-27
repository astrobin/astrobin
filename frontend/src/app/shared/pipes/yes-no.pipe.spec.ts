import { YesNoPipe } from "./yes-no.pipe";

describe("YesNoPipe", () => {
  it("create an instance", () => {
    const pipe = new YesNoPipe();

    expect(pipe).toBeTruthy();
  });

  it("should return 'yes' if true", () => {
    const pipe = new YesNoPipe();

    expect(pipe.transform(true)).toEqual("Yes");
  });

  it("should return 'no' if not true", () => {
    const pipe = new YesNoPipe();

    expect(pipe.transform(false)).toEqual("No");
    expect(pipe.transform(undefined)).toEqual("No");
    expect(pipe.transform(null)).toEqual("No");
  });
});
