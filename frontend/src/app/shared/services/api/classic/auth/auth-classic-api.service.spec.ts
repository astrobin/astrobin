import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { MockBuilder } from "ng-mocks";
import { AuthClassicApiService } from "./auth-classic-api.service";

describe("AuthApiService", () => {
  let service: AuthClassicApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => MockBuilder(AuthClassicApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule));

  beforeEach(() => {
    service = TestBed.inject(AuthClassicApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe("login", () => {
    it("should get a token", () => {
      const mockToken = "123";
      service.login("foo", "bar").subscribe(token => {
        expect(token).toEqual(mockToken);
      });

      const req = httpMock.expectOne(`${service.configUrl}/api-auth-token/`);
      expect(req.request.method).toBe("POST");
      req.flush({ token: mockToken });
    });
  });
});
