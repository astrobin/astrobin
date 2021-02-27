import { TestBed } from "@angular/core/testing";

import { AppModule } from "@app/app.module";
import { MockBuilder } from "ng-mocks";
import { PaymentsApiService } from "./payments-api.service";

describe("PaymentsApiService", () => {
  let service: PaymentsApiService;

  beforeEach(async () => {
    await MockBuilder(PaymentsApiService, AppModule);
    service = TestBed.inject(PaymentsApiService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });
});
