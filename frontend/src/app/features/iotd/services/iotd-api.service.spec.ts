import { TestBed } from "@angular/core/testing";

import { IotdModule } from "@features/iotd/iotd.module";
import { MockBuilder } from "ng-mocks";
import { IotdApiService } from "./iotd-api.service";

describe("IotdApiService", () => {
  let service: IotdApiService;

  beforeEach(async () => {
    await MockBuilder(IotdApiService, IotdModule);
    service = TestBed.inject(IotdApiService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });
});
