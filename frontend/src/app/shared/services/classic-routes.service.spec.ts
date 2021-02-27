import { TestBed } from "@angular/core/testing";
import { MockBuilder } from "ng-mocks";

import { ClassicRoutesService } from "./classic-routes.service";

describe("ClassicRoutesService", () => {
  beforeEach(() => MockBuilder(ClassicRoutesService));

  it("should be created", () => {
    const service: ClassicRoutesService = TestBed.inject(ClassicRoutesService);
    expect(service).toBeTruthy();
  });
});
