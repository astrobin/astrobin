import { LoadSubmissionQueue } from "@features/iotd/store/iotd.actions";

describe("Iotd", () => {
  it("should create an instance", () => {
    expect(new LoadSubmissionQueue()).toBeTruthy();
  });
});
