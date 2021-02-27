import * as fromSubmissionQueue from "./iotd.reducer";
import { selectIotdState } from "./iotd.selectors";

describe("Iotd Selectors", () => {
  it("should select the feature state", () => {
    const result = selectIotdState({
      [fromSubmissionQueue.iotdFeatureKey]: {}
    });

    expect(result).toEqual({});
  });
});
