import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { CameraGenerator } from "@shared/generators/camera.generator";
import { CameraApiService } from "@shared/services/api/classic/gear/camera/camera-api.service";
import { MockBuilder } from "ng-mocks";

describe("CameraApiService", () => {
  let service: CameraApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(CameraApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule);

    service = TestBed.inject(CameraApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("getCamera should work", () => {
    const camera = CameraGenerator.camera();

    service.getCamera(camera.pk).subscribe(response => {
      expect(response.pk).toEqual(camera.pk);
    });

    const req = httpMock.expectOne(`${service.configUrl}/${camera.pk}/`);
    expect(req.request.method).toBe("GET");
    req.flush(camera);
  });
});
