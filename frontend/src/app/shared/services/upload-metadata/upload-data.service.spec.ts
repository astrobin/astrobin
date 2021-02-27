import { TestBed } from "@angular/core/testing";
import { MockBuilder } from "ng-mocks";
import { skip } from "rxjs/operators";

import { UploadDataService, UploadMetadataEventInterface, UploadMetadataInterface } from "./upload-data.service";

describe("UploadMetadataService", () => {
  let service: UploadDataService;

  beforeEach(async () => {
    await MockBuilder(UploadDataService);
    service = TestBed.inject(UploadDataService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("setMetadata", () => {
    it("should emit metadata change", done => {
      const event: UploadMetadataEventInterface = {
        id: "foo",
        metadata: {
          bar: 99
        }
      };

      service.metadataChanges$.pipe(skip(1)).subscribe(value => {
        expect(value).toEqual(event);
        done();
      });

      service.setMetadata(event.id, event.metadata);
    });
  });

  describe("patchMetadata", () => {
    it("should emit metadata change", done => {
      const event: UploadMetadataEventInterface = {
        id: "foo",
        metadata: {
          bar: 99
        }
      };

      service.metadataChanges$.pipe(skip(1)).subscribe(value => {
        expect(value).toEqual(event);
        done();
      });

      service.setMetadata(event.id, event.metadata);
    });

    it("should patch data instead of replacing", done => {
      const metadata1: UploadMetadataInterface = {
        foo: "bar"
      };

      const metadata2: UploadMetadataInterface = {
        boo: "tar"
      };

      const event: UploadMetadataEventInterface = {
        id: "1",
        metadata: {
          foo: "bar",
          boo: "tar"
        }
      };

      service.metadataChanges$.pipe(skip(2)).subscribe(value => {
        expect(value).toEqual(event);
        done();
      });

      service.setMetadata(event.id, metadata1);
      service.patchMetadata(event.id, metadata2);
    });
  });

  describe("setEndpoint", () => {
    it("should emit endpoint change", done => {
      service.endpointChanges$.pipe(skip(1)).subscribe(value => {
        expect(value).toEqual("foo");
        done();
      });

      service.setEndpoint("foo");
    });
  });
});
