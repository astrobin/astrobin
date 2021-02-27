import { TestBed } from "@angular/core/testing";
import { WindowRefService } from "@shared/services/window-ref.service";
import { MockBuilder } from "ng-mocks";

describe(`WindowRefService`, () => {
  let service: WindowRefService;

  beforeEach(async () => {
    await MockBuilder(WindowRefService);
    service = TestBed.inject(WindowRefService);
  });

  it("should get the window", () => {
    expect(service.nativeWindow).not.toBeUndefined();
  });
});
