from gql import gql

VISITOR_REVIEW_PHOTOS = gql("""
query getVisitorReviewPhotosInVisitorReviewTab($input: VisitorReviewPhotosInput) {
  visitorReviewPhotos(input: $input) {
    viewId
    originalUrl
    photoType
    mediaType
    logId
    relation
    title
    text
    date
    link
    sourceTitle
    externalLink {
      title
      url
    }
    author {
      id
      nickname
      from
      imageUrl
      objectId
      url
      borderImageUrl
    }
    votedKeywords {
      code
      iconUrl
      iconCode
      name
    }
    visitCount
    originType
    isFollowing
    rating
    video {
      videoId
      videoUrl
      trailerUrl
    }
  }
}
""")

PHOTO_VIEWER = gql("""
query getPhotoViewerItems($input: PhotoViewerInput, $isNmap: Boolean = false) {
  photoViewer(input: $input) {
    cursors {
      id
      startIndex
      hasNext
      lastCursor
    }
    photos {
      viewId
      originalUrl
      originalDate
      width
      height
      title
      text
      desc
      link
      date
      photoType
      mediaType
      option {
        channelName
        dateString
        playCount
        likeCount
      }
      to
      relation
      logId
      author {
        id
        nickname
        from
        imageUrl
        objectId
        url
        borderImageUrl
        officialYn
      }
      votedKeywords {
        code
        iconUrl
        iconCode
        name
      }
      visitCount
      originType
      isFollowing
      businessName
      rating
      externalLink {
        title
        url
      }
      sourceTitle
      moment {
        channelId
        contentId
        momentId
        gdid
        blogRelation
        statAllowYn
        category
        docNo
      }
      video {
        videoId
        videoUrl
        trailerUrl
      }
      music {
        artists
        title
      }
      clip {
        serviceType
        createdAt
        contentType
      }
    }
  }
}
""")

FOLLOWING_REVIEWS = gql("""
query getFollowingReviews($input: FollowingReviewsInput) {
  followingReviews(input: $input) {
    reviews {
      id
      apolloCacheId
      rating
      author {
        id
        nickname
        from
        imageUrl
        objectId
        url
        review {
          totalCount
          imageCount
          avgRating
        }
        theme {
          totalCount
        }
        isFollowing
        followerCount
        followRequested
      }
      body
      thumbnail
      media {
        type
        thumbnail
        thumbnailRatio
        class
        videoId
        videoUrl
        trailerUrl
      }
      tags
      status
      visitCount
      viewCount
      visited
      created
      reply {
        editUrl
        body
        editedBy
        created
        date
        replyTitle
        isReported
        isSuspended
        status
      }
      originType
      item {
        name
        code
        options
      }
      businessName
      votedKeywords {
        code
        iconCode
        name
        iconUrl
      }
      visitCategories {
        code
        name
        keywords {
          code
          name
        }
      }
      userIdno
      loginIdno
      reactionStat {
        id
        typeCount {
          name
          count
        }
        totalCount
      }
      hasViewerReacted {
        id
        reacted
      }
      nickname
      representativeVisitDateTime
    }
    reactionTypes {
      name
      emojiUrl
      label
    }
  }
}
""")

VISITOR_REVIEWS = gql("""
query getVisitorReviews($input: VisitorReviewsInput) {
  visitorReviews(input: $input) {
    items {
      id
      cursor
      reviewId
      rating
      author {
        id
        nickname
        from
        imageUrl
        borderImageUrl
        objectId
        url
        review {
          totalCount
          imageCount
          avgRating
        }
        theme {
          totalCount
        }
        isFollowing
        followerCount
        followRequested
      }
      body
      thumbnail
      media {
        type
        thumbnail
        thumbnailRatio
        class
        videoId
        videoUrl
        trailerUrl
      }
      tags
      status
      visitCount
      viewCount
      visited
      created
      reply {
        editUrl
        body
        editedBy
        created
        date
        replyTitle
        isReported
        isSuspended
        status
      }
      originType
      item {
        name
        code
        options
      }
      language
      highlightRanges {
        start
        end
      }
      apolloCacheId
      translatedText
      businessName
      showBookingItemName
      bookingItemName
      votedKeywords {
        code
        iconUrl
        iconCode
        name
      }
      userIdno
      loginIdno
      receiptInfoUrl
      reactionStat {
        id
        typeCount {
          name
          count
        }
        totalCount
      }
      hasViewerReacted {
        id
        reacted
      }
      nickname
      showPaymentInfo
      visitCategories {
        code
        name
        keywords {
          code
          name
        }
      }
      representativeVisitDateTime
      showRepresentativeVisitDateTime
    }
    starDistribution {
      score
      count
    }
    hideProductSelectBox
    total
    showRecommendationSort
    itemReviewStats {
      score
      count
      itemId
      starDistribution {
        score
        count
      }
    }
  }
}
""")

VISITOR_REVIEW_THEME_LISTS = gql("""
query getVisitorReviewThemeLists($input: ThemeListsInput) {
  themeLists(input: $input) {
    themeLists {
      id
      title
      viewCount
      itemCount
      reviews {
        businessName
        reviewBody
        imageUrl
      }
      authorNickname
      authorImageUrl
      isFollowing
      themeListUrl
      authorUrl
      cursor
    }
    total
  }
}
""")
