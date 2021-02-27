import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { environment } from "@env/environment";
import { ImageThumbnailGenerator } from "@shared/generators/image-thumbnail.generator";
import { ImageGenerator } from "@shared/generators/image.generator";
import { TelescopeGenerator } from "@shared/generators/telescope.generator";
import { TelescopeApiService } from "@shared/services/api/classic/gear/telescope/telescope-api.service";
import { MockBuilder } from "ng-mocks";

describe("TelescopeApiService", () => {
  let service: TelescopeApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(TelescopeApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule);

    service = TestBed.inject(TelescopeApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("getTelescope should work", () => {
    const telescope = TelescopeGenerator.telescope();

    service.getTelescope(telescope.pk).subscribe(response => {
      expect(response.pk).toEqual(telescope.pk);
    });

    const req = httpMock.expectOne(`${service.configUrl}/${telescope.pk}/`);
    expect(req.request.method).toBe("GET");
    req.flush(telescope);
  });
});
