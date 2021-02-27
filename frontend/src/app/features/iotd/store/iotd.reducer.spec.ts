import { initialIotdState, reducer } from "./iotd.reducer";

describe("Iotd Reducer", () => {
  describe("an unknown action", () => {
    it("should return the previous state", () => {
      const action = {} as any;

      const result = reducer(initialIotdState, action);

      expect(result).toBe(initialIotdState);
    });
  });
});
