import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { environment } from "@env/environment";
import { ImageAlias } from "@shared/enums/image-alias.enum";
import { ImageThumbnailGenerator } from "@shared/generators/image-thumbnail.generator";
import { ImageGenerator } from "@shared/generators/image.generator";
import { MockBuilder } from "ng-mocks";
import { ImageApiService } from "./image-api.service";

describe("ImageApiService", () => {
  let service: ImageApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(ImageApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule);

    service = TestBed.inject(ImageApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("getImage should work", () => {
    const image = ImageGenerator.image();

    service.getImage(image.pk).subscribe(response => {
      expect(response.pk).toEqual(image.pk);
    });

    const req = httpMock.expectOne(`${service.configUrl}/image/${image.pk}/`);
    expect(req.request.method).toBe("GET");
    req.flush(image);
  });

  it("getImages should work", () => {
    const images = [ImageGenerator.image({ pk: 1 }), ImageGenerator.image({ pk: 2 })];

    service.getImages([images[0].pk, images[1].pk]).subscribe(response => {
      expect(response.results[0]).toEqual(images[0]);
      expect(response.results[1]).toEqual(images[1]);
    });

    const req = httpMock.expectOne(`${service.configUrl}/image/?ids=1,2`);
    expect(req.request.method).toBe("GET");
    req.flush({ results: images });
  });

  it("getThumbnail should work", () => {
    const image = ImageGenerator.image();

    service.getThumbnail(image.hash, "final", ImageAlias.REGULAR).subscribe(response => {
      expect(response.url).toEqual("/foo");
      expect(response.id).toEqual(image.pk);
      expect(response.revision).toEqual("final");
      expect(response.alias).toEqual("regular");
    });

    const req = httpMock.expectOne(`${environment.classicBaseUrl}/${image.hash}/final/thumb/regular/`);
    expect(req.request.method).toBe("GET");
    req.flush(
      ImageThumbnailGenerator.thumbnail({
        url: "/foo",
        id: image.pk,
        revision: "final",
        alias: ImageAlias.REGULAR
      })
    );
  });
});
