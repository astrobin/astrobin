import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { Constants } from "@shared/constants";
import { ImageGenerator } from "@shared/generators/image.generator";
import { ThumbnailGroupGenerator } from "@shared/generators/thumbnail-group.generator";
import { MockBuilder } from "ng-mocks";
import { ThumbnailGroupApiService } from "./thumbnail-group-api.service";

describe("ThumbnailGroupApiService", () => {
  let service: ThumbnailGroupApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(ThumbnailGroupApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule);

    service = TestBed.inject(ThumbnailGroupApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("getThumbnailGroup should work", () => {
    const image = ImageGenerator.image();
    const thumbnailGroup = ThumbnailGroupGenerator.thumbnailGroup();

    service.getThumbnailGroup(image.pk, Constants.ORIGINAL_REVISION).subscribe(response => {
      expect(response.image).toEqual(image.pk);
    });

    const req = httpMock.expectOne(`${service.configUrl}/?image=${image.pk}`);
    expect(req.request.method).toBe("GET");
    req.flush(image);
  });
});
