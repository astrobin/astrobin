import { TestBed } from "@angular/core/testing";

import { SolutionGenerator } from "@shared/generators/solution.generator";
import { SolutionService } from "./solution.service";

describe("SolutionService", () => {
  let service: SolutionService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SolutionService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("getObjectsInField", () => {
    it("should work", () => {
      const solution = SolutionGenerator.solution();
      solution.objects_in_field = "M1, M2, M3";

      expect(service.getObjectsInField(solution)).toEqual(["M1", "M2", "M3"]);
    });
  });
});
