import { TestBed } from "@angular/core/testing";
import { LoadingService } from "@shared/services/loading.service";
import { MockBuilder } from "ng-mocks";

describe(`LoadingService`, () => {
  let service: LoadingService;

  beforeEach(async () => {
    await MockBuilder(LoadingService);
    service = TestBed.inject(LoadingService);
  });

  it("should set the loading state correctly", () => {
    service.setLoading(true);

    expect(service.isLoading()).toBe(true);

    service.setLoading(false);

    expect(service.isLoading()).toBe(false);
  });
});
