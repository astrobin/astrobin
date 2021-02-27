import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { MockBuilder } from "ng-mocks";
import { JsonApiService } from "./json-api.service";

describe("JsonApiService", () => {
  let service: JsonApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(JsonApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule);

    service = TestBed.inject(JsonApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("getBackendConfig", () => {
    it("should work", () => {
      service.getBackendConfig().subscribe(response => {
        expect(response.readOnly).toEqual(false);
      });

      const req = httpMock.expectOne(`${service.configUrl}/common/app-config/`);
      expect(req.request.method).toBe("GET");
      req.flush({ readOnly: false });
    });
  });
});
