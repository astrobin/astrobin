class License:
    ALL_RIGHTS_RESERVED = 'ALL_RIGHTS_RESERVED'
    ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE = 'ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE'
    ATTRIBUTION_NON_COMMERCIAL = 'ATTRIBUTION_NON_COMMERCIAL'
    ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS = 'ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS'
    ATTRIBUTION = 'ATTRIBUTION'
    ATTRIBUTION_SHARE_ALIKE = 'ATTRIBUTION_SHARE_ALIKE'
    ATTRIBUTION_NO_DERIVS = 'ATTRIBUTION_NO_DERIVS'

    @staticmethod
    def to_deprecated_integer(license):
        # type: (License) -> int

        return {
            License.ALL_RIGHTS_RESERVED: 0,
            License.ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE: 1,
            License.ATTRIBUTION_NON_COMMERCIAL: 2,
            License.ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS: 3,
            License.ATTRIBUTION: 4,
            License.ATTRIBUTION_SHARE_ALIKE: 5,
            License.ATTRIBUTION_NO_DERIVS: 6,
        }[license]

    @staticmethod
    def from_deprecated_integer(license):
        # type: (int) -> License

        return {
            0: License.ALL_RIGHTS_RESERVED,
            1: License.ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE,
            2: License.ATTRIBUTION_NON_COMMERCIAL,
            3: License.ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS,
            4: License.ATTRIBUTION,
            5: License.ATTRIBUTION_SHARE_ALIKE,
            6: License.ATTRIBUTION_NO_DERIVS,
        }[license]
